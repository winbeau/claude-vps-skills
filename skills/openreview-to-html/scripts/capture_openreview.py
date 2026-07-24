#!/usr/bin/env python3
"""Capture an authenticated OpenReview forum from interactive Linux Chrome.

This helper never reads browser profiles, cookies, tokens, storage, or network
traffic. It uses X11/XTest keyboard shortcuts and the desktop clipboard after a
human completes OpenReview verification or login.
"""

from __future__ import annotations

import argparse
import ctypes
import ctypes.util
import html.parser
import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from urllib.parse import parse_qs, urlencode, urljoin, urlparse

ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")
EMAIL_ONLY_RE = re.compile(r"^\s*[^\s@]+@[^\s@]+\.[^\s@]+\s*$")
VERIFY_MARKERS = (
    "verifying your browser",
    "complete the check below",
    "please complete the verification",
    "verification failed to load",
)
HIDDEN_CONTENT_MARKERS = (
    "load more",
    "show more replies",
    "view more replies",
    "expand replies",
)
NOTE_HEADING_RE = re.compile(
    r"(?im)^(?:official review|meta review|metareview|decision|author response|"
    r"rebuttal|comment|withdrawal|revision)(?:\s|:|of|by)"
)
TOP_LEVEL_REPLY_RE = re.compile(
    r"(?im)^(?:Official Review of Submission|Meta Review of Submission|"
    r"Decision of Submission|Author Response(?: of Submission| to )?|"
    r"Rebuttal(?: of Submission| to )?|Comment(?: of Submission| by )|"
    r"Withdrawal of Submission|Revision of Submission)"
)
REPLY_COUNT_RE = re.compile(r"(?im)\b(\d+)\s*/\s*(\d+)\s+replies\s+shown\b")
CHROME_NAMES = ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser")


class CaptureError(RuntimeError):
    """An actionable capture failure."""


@dataclass(frozen=True)
class OpenReviewURL:
    original: str
    forum_id: str
    note_id: str | None

    @property
    def canonical_forum_url(self) -> str:
        return "https://openreview.net/forum?" + urlencode({"id": self.forum_id})

    @property
    def canonical_url(self) -> str:
        query = {"id": self.forum_id}
        if self.note_id:
            query["noteId"] = self.note_id
        return "https://openreview.net/forum?" + urlencode(query)


@dataclass(frozen=True)
class WindowInfo:
    window_id: int
    title: str
    instance: str
    class_name: str
    pid: int | None
    width: int
    height: int

    @property
    def hex_id(self) -> str:
        return hex(self.window_id)


@dataclass(frozen=True)
class CapturedLink:
    text: str
    url: str
    forum_id: str
    note_id: str | None


def parse_openreview_url(raw: str) -> OpenReviewURL:
    value = raw.strip()
    parsed = urlparse(value)
    if parsed.scheme != "https":
        raise CaptureError("OpenReview URL must use https")
    if (parsed.hostname or "").lower() != "openreview.net" or parsed.port is not None:
        raise CaptureError("OpenReview URL host must be exactly openreview.net")
    if parsed.path.rstrip("/") != "/forum":
        raise CaptureError("OpenReview URL path must be /forum")
    if parsed.fragment:
        raise CaptureError("OpenReview URL must not contain a fragment")

    query = parse_qs(parsed.query, keep_blank_values=True)
    unknown_duplicates = [key for key, values in query.items() if len(values) != 1]
    if unknown_duplicates:
        raise CaptureError(f"URL query parameter must occur once: {unknown_duplicates[0]}")
    ids = query.get("id", [])
    if len(ids) != 1 or not ids[0]:
        raise CaptureError("OpenReview URL must contain exactly one non-empty id")
    forum_id = ids[0]
    if not ID_RE.fullmatch(forum_id):
        raise CaptureError("OpenReview forum id contains unsupported characters")

    notes = query.get("noteId", [])
    if len(notes) > 1 or (notes and not notes[0]):
        raise CaptureError("noteId must occur at most once and be non-empty")
    note_id = notes[0] if notes else None
    if note_id and not ID_RE.fullmatch(note_id):
        raise CaptureError("OpenReview noteId contains unsupported characters")
    return OpenReviewURL(value, forum_id, note_id)


def find_chrome() -> str:
    for name in CHROME_NAMES:
        path = shutil.which(name)
        if path:
            return path
    raise CaptureError("Linux Chrome/Chromium was not found in PATH")


def require_xclip() -> str:
    path = shutil.which("xclip")
    if not path:
        raise CaptureError("xclip was not found; install it or use the manual fallback")
    return path


def write_private_json(path: Path, payload: dict) -> None:
    path = path.expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    fd = os.open(path, flags, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
    except Exception:
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        raise


class XWindowAttributes(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_int),
        ("y", ctypes.c_int),
        ("width", ctypes.c_int),
        ("height", ctypes.c_int),
        ("border_width", ctypes.c_int),
        ("depth", ctypes.c_int),
        ("visual", ctypes.c_void_p),
        ("root", ctypes.c_ulong),
        ("class_", ctypes.c_int),
        ("bit_gravity", ctypes.c_int),
        ("win_gravity", ctypes.c_int),
        ("backing_store", ctypes.c_int),
        ("backing_planes", ctypes.c_ulong),
        ("backing_pixel", ctypes.c_ulong),
        ("save_under", ctypes.c_int),
        ("colormap", ctypes.c_ulong),
        ("map_installed", ctypes.c_int),
        ("map_state", ctypes.c_int),
        ("all_event_masks", ctypes.c_long),
        ("your_event_mask", ctypes.c_long),
        ("do_not_propagate_mask", ctypes.c_long),
        ("override_redirect", ctypes.c_int),
        ("screen", ctypes.c_void_p),
    ]


class XClassHint(ctypes.Structure):
    _fields_ = [("res_name", ctypes.c_void_p), ("res_class", ctypes.c_void_p)]


class XClientMessageData(ctypes.Union):
    _fields_ = [
        ("b", ctypes.c_char * 20),
        ("s", ctypes.c_short * 10),
        ("l", ctypes.c_long * 5),
    ]


class XClientMessageEvent(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_int),
        ("serial", ctypes.c_ulong),
        ("send_event", ctypes.c_int),
        ("display", ctypes.c_void_p),
        ("window", ctypes.c_ulong),
        ("message_type", ctypes.c_ulong),
        ("format", ctypes.c_int),
        ("data", XClientMessageData),
    ]


class X11Controller:
    IS_VIEWABLE = 2
    REVERT_TO_PARENT = 2
    CURRENT_TIME = 0
    CLIENT_MESSAGE = 33
    SUBSTRUCTURE_NOTIFY_MASK = 1 << 19
    SUBSTRUCTURE_REDIRECT_MASK = 1 << 20

    def __init__(self) -> None:
        if not os.environ.get("DISPLAY"):
            raise CaptureError("$DISPLAY is missing; X11 capture is unavailable")
        x11_name = ctypes.util.find_library("X11")
        xtst_name = ctypes.util.find_library("Xtst")
        if not x11_name:
            raise CaptureError("libX11 was not found")
        if not xtst_name:
            raise CaptureError("libXtst was not found")
        self.x = ctypes.CDLL(x11_name)
        self.t = ctypes.CDLL(xtst_name)
        self._configure()
        self.display = self.x.XOpenDisplay(None)
        if not self.display:
            raise CaptureError(f"could not open X11 display {os.environ.get('DISPLAY')}")
        self.root = self.x.XDefaultRootWindow(self.display)

    def _configure(self) -> None:
        display = ctypes.c_void_p
        window = ctypes.c_ulong
        self.x.XOpenDisplay.argtypes = [ctypes.c_char_p]
        self.x.XOpenDisplay.restype = display
        self.x.XDefaultRootWindow.argtypes = [display]
        self.x.XDefaultRootWindow.restype = window
        self.x.XQueryTree.argtypes = [
            display,
            window,
            ctypes.POINTER(window),
            ctypes.POINTER(window),
            ctypes.POINTER(ctypes.POINTER(window)),
            ctypes.POINTER(ctypes.c_uint),
        ]
        self.x.XQueryTree.restype = ctypes.c_int
        self.x.XFetchName.argtypes = [display, window, ctypes.POINTER(ctypes.c_char_p)]
        self.x.XFetchName.restype = ctypes.c_int
        self.x.XGetClassHint.argtypes = [display, window, ctypes.POINTER(XClassHint)]
        self.x.XGetClassHint.restype = ctypes.c_int
        self.x.XGetWindowAttributes.argtypes = [display, window, ctypes.POINTER(XWindowAttributes)]
        self.x.XGetWindowAttributes.restype = ctypes.c_int
        self.x.XInternAtom.argtypes = [display, ctypes.c_char_p, ctypes.c_int]
        self.x.XInternAtom.restype = ctypes.c_ulong
        self.x.XSendEvent.argtypes = [display, window, ctypes.c_int, ctypes.c_long, ctypes.c_void_p]
        self.x.XSendEvent.restype = ctypes.c_int
        self.x.XGetWindowProperty.argtypes = [
            display,
            window,
            ctypes.c_ulong,
            ctypes.c_long,
            ctypes.c_long,
            ctypes.c_int,
            ctypes.c_ulong,
            ctypes.POINTER(ctypes.c_ulong),
            ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_ulong),
            ctypes.POINTER(ctypes.c_ulong),
            ctypes.POINTER(ctypes.POINTER(ctypes.c_ubyte)),
        ]
        self.x.XGetWindowProperty.restype = ctypes.c_int
        self.x.XRaiseWindow.argtypes = [display, window]
        self.x.XMapRaised.argtypes = [display, window]
        self.x.XSetInputFocus.argtypes = [display, window, ctypes.c_int, ctypes.c_ulong]
        self.x.XWarpPointer.argtypes = [
            display,
            window,
            window,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_uint,
            ctypes.c_uint,
            ctypes.c_int,
            ctypes.c_int,
        ]
        self.x.XStringToKeysym.argtypes = [ctypes.c_char_p]
        self.x.XStringToKeysym.restype = ctypes.c_ulong
        self.x.XKeysymToKeycode.argtypes = [display, ctypes.c_ulong]
        self.x.XKeysymToKeycode.restype = ctypes.c_ubyte
        self.x.XFlush.argtypes = [display]
        self.x.XSync.argtypes = [display, ctypes.c_int]
        self.x.XFree.argtypes = [ctypes.c_void_p]
        self.x.XCloseDisplay.argtypes = [display]
        self.t.XTestFakeKeyEvent.argtypes = [display, ctypes.c_uint, ctypes.c_int, ctypes.c_ulong]
        self.t.XTestFakeKeyEvent.restype = ctypes.c_int
        self.t.XTestFakeButtonEvent.argtypes = [display, ctypes.c_uint, ctypes.c_int, ctypes.c_ulong]
        self.t.XTestFakeButtonEvent.restype = ctypes.c_int

    def close(self) -> None:
        if getattr(self, "display", None):
            self.x.XCloseDisplay(self.display)
            self.display = None

    def __enter__(self) -> "X11Controller":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _utf8_property(self, window_id: int, property_name: bytes) -> str:
        property_atom = self.x.XInternAtom(self.display, property_name, False)
        utf8_atom = self.x.XInternAtom(self.display, b"UTF8_STRING", False)
        actual = ctypes.c_ulong()
        fmt = ctypes.c_int()
        count = ctypes.c_ulong()
        remaining = ctypes.c_ulong()
        data = ctypes.POINTER(ctypes.c_ubyte)()
        status = self.x.XGetWindowProperty(
            self.display,
            window_id,
            property_atom,
            0,
            4096,
            False,
            utf8_atom,
            ctypes.byref(actual),
            ctypes.byref(fmt),
            ctypes.byref(count),
            ctypes.byref(remaining),
            ctypes.byref(data),
        )
        if status != 0 or not data or fmt.value != 8 or count.value < 1:
            return ""
        try:
            return ctypes.string_at(data, count.value).decode("utf-8", errors="replace")
        finally:
            self.x.XFree(data)

    def _title(self, window_id: int) -> str:
        modern = self._utf8_property(window_id, b"_NET_WM_NAME")
        if modern:
            return modern
        name = ctypes.c_char_p()
        if self.x.XFetchName(self.display, window_id, ctypes.byref(name)) and name.value:
            try:
                return name.value.decode("utf-8", errors="replace")
            finally:
                self.x.XFree(name)
        return ""

    def _class_hint(self, window_id: int) -> tuple[str, str]:
        hint = XClassHint()
        if not self.x.XGetClassHint(self.display, window_id, ctypes.byref(hint)):
            return "", ""
        try:
            instance = ctypes.string_at(hint.res_name).decode(errors="replace") if hint.res_name else ""
            class_name = ctypes.string_at(hint.res_class).decode(errors="replace") if hint.res_class else ""
            return instance, class_name
        finally:
            if hint.res_name:
                self.x.XFree(hint.res_name)
            if hint.res_class:
                self.x.XFree(hint.res_class)

    def _pid(self, window_id: int) -> int | None:
        atom = self.x.XInternAtom(self.display, b"_NET_WM_PID", False)
        actual = ctypes.c_ulong()
        fmt = ctypes.c_int()
        count = ctypes.c_ulong()
        remaining = ctypes.c_ulong()
        data = ctypes.POINTER(ctypes.c_ubyte)()
        status = self.x.XGetWindowProperty(
            self.display,
            window_id,
            atom,
            0,
            1,
            False,
            6,  # XA_CARDINAL
            ctypes.byref(actual),
            ctypes.byref(fmt),
            ctypes.byref(count),
            ctypes.byref(remaining),
            ctypes.byref(data),
        )
        if status != 0 or not data or count.value < 1:
            return None
        try:
            return int(ctypes.cast(data, ctypes.POINTER(ctypes.c_ulong))[0])
        finally:
            self.x.XFree(data)

    def _children(self, window_id: int) -> list[int]:
        root = ctypes.c_ulong()
        parent = ctypes.c_ulong()
        children = ctypes.POINTER(ctypes.c_ulong)()
        count = ctypes.c_uint()
        if not self.x.XQueryTree(
            self.display,
            window_id,
            ctypes.byref(root),
            ctypes.byref(parent),
            ctypes.byref(children),
            ctypes.byref(count),
        ):
            return []
        try:
            return [int(children[index]) for index in range(count.value)]
        finally:
            if children:
                self.x.XFree(children)

    def windows(self) -> list[WindowInfo]:
        found: list[WindowInfo] = []
        stack = list(reversed(self._children(self.root)))
        seen: set[int] = set()
        while stack:
            window_id = stack.pop()
            if window_id in seen:
                continue
            seen.add(window_id)
            stack.extend(reversed(self._children(window_id)))
            title = self._title(window_id)
            if "openreview" not in title.lower():
                continue
            instance, class_name = self._class_hint(window_id)
            if "chrome" not in f"{instance} {class_name}".lower() and "chromium" not in f"{instance} {class_name}".lower():
                continue
            attrs = XWindowAttributes()
            if not self.x.XGetWindowAttributes(self.display, window_id, ctypes.byref(attrs)):
                continue
            if attrs.map_state != self.IS_VIEWABLE or attrs.width < 300 or attrs.height < 200:
                continue
            found.append(
                WindowInfo(
                    window_id,
                    title,
                    instance,
                    class_name,
                    self._pid(window_id),
                    attrs.width,
                    attrs.height,
                )
            )
        return sorted(found, key=lambda item: item.window_id)

    def activate(self, window_id: int, delay: float) -> None:
        active_atom = self.x.XInternAtom(self.display, b"_NET_ACTIVE_WINDOW", False)
        event = XClientMessageEvent()
        event.type = self.CLIENT_MESSAGE
        event.send_event = True
        event.display = self.display
        event.window = window_id
        event.message_type = active_atom
        event.format = 32
        event.data.l[0] = 2  # source indication: pager/tool
        event.data.l[1] = self.CURRENT_TIME
        event.data.l[2] = 0
        self.x.XSendEvent(
            self.display,
            self.root,
            False,
            self.SUBSTRUCTURE_REDIRECT_MASK | self.SUBSTRUCTURE_NOTIFY_MASK,
            ctypes.byref(event),
        )
        self.x.XMapRaised(self.display, window_id)
        self.x.XRaiseWindow(self.display, window_id)
        self.x.XSetInputFocus(
            self.display,
            window_id,
            self.REVERT_TO_PARENT,
            self.CURRENT_TIME,
        )
        self.x.XSync(self.display, False)
        time.sleep(delay)

    def click_document(self, window: WindowInfo) -> None:
        x = max(20, min(window.width - 20, window.width // 3))
        y = max(100, min(window.height - 20, window.height // 3))
        self.x.XWarpPointer(self.display, 0, window.window_id, 0, 0, 0, 0, x, y)
        self.x.XSync(self.display, False)
        if not self.t.XTestFakeButtonEvent(self.display, 1, True, self.CURRENT_TIME):
            raise CaptureError("XTest failed while focusing the Chrome document")
        if not self.t.XTestFakeButtonEvent(self.display, 1, False, self.CURRENT_TIME):
            raise CaptureError("XTest failed while focusing the Chrome document")
        self.x.XSync(self.display, False)

    def _key(self, name: str, pressed: bool) -> None:
        keysym = self.x.XStringToKeysym(name.encode("ascii"))
        if not keysym:
            raise CaptureError(f"X11 keysym is unavailable: {name}")
        keycode = self.x.XKeysymToKeycode(self.display, keysym)
        if not keycode:
            raise CaptureError(f"X11 keycode is unavailable: {name}")
        if not self.t.XTestFakeKeyEvent(self.display, keycode, bool(pressed), self.CURRENT_TIME):
            raise CaptureError(f"XTest failed while sending key: {name}")
        self.x.XFlush(self.display)

    def press(self, name: str) -> None:
        self._key(name, True)
        self._key(name, False)

    def chord(self, modifier: str, key: str) -> None:
        self._key(modifier, True)
        self._key(key, True)
        self._key(key, False)
        self._key(modifier, False)


def clipboard_read(target: str | None = None) -> str:
    command = [require_xclip(), "-selection", "clipboard", "-o"]
    if target:
        command[3:3] = ["-t", target]
    result = subprocess.run(command, capture_output=True, timeout=8)
    if result.returncode != 0:
        return ""
    return result.stdout.decode("utf-8", errors="replace")


def clipboard_write(text: str) -> None:
    command = [require_xclip(), "-selection", "clipboard", "-i"]
    subprocess.run(command, input=text.encode("utf-8"), check=True, timeout=8)


def clipboard_targets() -> list[str]:
    raw = clipboard_read("TARGETS")
    return [line.strip() for line in raw.splitlines() if line.strip()]


class LinkParser(html.parser.HTMLParser):
    def __init__(self, base_url: str, forum_id: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.forum_id = forum_id
        self.current_href: str | None = None
        self.current_text: list[str] = []
        self.links: list[CapturedLink] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        href = dict(attrs).get("href")
        self.current_href = urljoin(self.base_url, href) if href else None
        self.current_text = []

    def handle_data(self, data: str) -> None:
        if self.current_href:
            self.current_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "a" or not self.current_href:
            return
        try:
            parsed = parse_openreview_url(self.current_href)
        except CaptureError:
            self.current_href = None
            self.current_text = []
            return
        if parsed.forum_id == self.forum_id:
            self.links.append(
                CapturedLink(
                    " ".join("".join(self.current_text).split()),
                    parsed.canonical_url,
                    parsed.forum_id,
                    parsed.note_id,
                )
            )
        self.current_href = None
        self.current_text = []


def extract_links(rich_html: str, base_url: str, forum_id: str) -> list[CapturedLink]:
    if not rich_html:
        return []
    parser = LinkParser(base_url, forum_id)
    try:
        parser.feed(rich_html)
        parser.close()
    except html.parser.HTMLParseError:
        return []
    unique: dict[str, CapturedLink] = {}
    for link in parser.links:
        unique.setdefault(link.url, link)
    return list(unique.values())


def validate_page_text(text: str, expected: OpenReviewURL, links: Iterable[CapturedLink]) -> dict:
    stripped = text.strip()
    lower = stripped.lower()
    if not stripped or len(stripped) < 500:
        raise CaptureError("captured page text is implausibly short")
    if EMAIL_ONLY_RE.fullmatch(stripped):
        raise CaptureError("clipboard contains only an email address, not the forum page")
    if stripped.startswith(("https://openreview.net/", "http://openreview.net/")) and "\n" not in stripped:
        raise CaptureError("clipboard contains only the address bar URL, not the forum page")
    marker = next((item for item in VERIFY_MARKERS if item in lower), None)
    if marker:
        raise CaptureError(f"OpenReview verification/login is incomplete: {marker}")
    hidden = [item for item in HIDDEN_CONTENT_MARKERS if item in lower]
    if hidden:
        raise CaptureError(f"discussion still contains hidden-content control: {hidden[0]}")
    if "openreview" not in lower or "discussion" not in lower:
        raise CaptureError("captured text does not look like an OpenReview forum")

    note_ids = {link.note_id for link in links if link.note_id}
    if expected.note_id and expected.note_id not in note_ids:
        # The address itself proves selection, but the rendered page must also contain a discussion.
        if not NOTE_HEADING_RE.search(stripped):
            raise CaptureError(f"requested noteId {expected.note_id} is not represented in the discussion")

    count_match = REPLY_COUNT_RE.search(stripped)
    heading_count = len(TOP_LEVEL_REPLY_RE.findall(stripped))
    count_check: dict[str, int | bool | None] = {
        "displayed": None,
        "total": None,
        "recognized_note_headings": heading_count,
        "matched": None,
    }
    if count_match:
        displayed, total = (int(value) for value in count_match.groups())
        count_check.update(displayed=displayed, total=total)
        if displayed == total and heading_count and heading_count != displayed:
            raise CaptureError(
                f"reply count says {displayed} replies, but {heading_count} note headings were captured"
            )
        count_check["matched"] = not heading_count or heading_count == displayed
    return {
        "characters": len(stripped),
        "lines": len(stripped.splitlines()),
        "note_links": len(note_ids),
        "reply_count": count_check,
        "hidden_controls": [],
    }


def choose_window(windows: list[WindowInfo], requested_id: str | None) -> WindowInfo:
    if requested_id:
        try:
            value = int(requested_id, 0)
        except ValueError as exc:
            raise CaptureError("--window-id must be a decimal or 0x-prefixed integer") from exc
        matches = [window for window in windows if window.window_id == value]
        if not matches:
            raise CaptureError(f"OpenReview Chrome window was not found: {requested_id}")
        return matches[0]
    if not windows:
        raise CaptureError("no visible Linux Chrome window with an OpenReview title was found")
    if len(windows) > 1:
        choices = "\n".join(f"  {item.hex_id}  {item.title}" for item in windows)
        raise CaptureError("multiple OpenReview Chrome windows match; rerun with --window-id:\n" + choices)
    return windows[0]


def capture_authenticated(args: argparse.Namespace) -> None:
    expected = parse_openreview_url(args.expected_url)
    requested_urls = [expected]
    for raw in args.note_url:
        parsed = parse_openreview_url(raw)
        if parsed.forum_id != expected.forum_id:
            raise CaptureError(f"additional note URL belongs to another forum: {raw}")
        requested_urls.append(parsed)
    require_xclip()
    previous_clipboard = clipboard_read()
    try:
        with X11Controller() as controller:
            target = choose_window(controller.windows(), args.window_id)
            controller.activate(target.window_id, args.focus_delay)

            sentinel = f"openreview-to-html:{os.getpid()}:{time.monotonic_ns()}"
            clipboard_write(sentinel)
            controller.chord("Control_L", "l")
            time.sleep(args.copy_delay)
            controller.chord("Control_L", "c")
            time.sleep(args.copy_delay)
            captured_url_text = clipboard_read().strip()
            if not captured_url_text or captured_url_text == sentinel:
                raise CaptureError("Chrome address copy did not reach the clipboard")
            captured_url = parse_openreview_url(captured_url_text)
            if captured_url.forum_id != expected.forum_id:
                raise CaptureError(
                    f"active Chrome forum is {captured_url.forum_id}, expected {expected.forum_id}"
                )
            if expected.note_id and captured_url.note_id != expected.note_id:
                raise CaptureError(
                    f"active URL noteId is {captured_url.note_id or '<none>'}, expected {expected.note_id}"
                )

            clipboard_write(sentinel)
            controller.press("Escape")
            time.sleep(args.focus_delay)
            controller.click_document(target)
            time.sleep(args.focus_delay)
            controller.chord("Control_L", "a")
            time.sleep(args.copy_delay)
            controller.chord("Control_L", "c")
            time.sleep(args.copy_delay)
            page_text = clipboard_read()
            if page_text.strip() == sentinel:
                raise CaptureError("Chrome page copy did not reach the clipboard")

            targets = clipboard_targets()
            rich_target = next(
                (item for item in targets if item.lower() in {"text/html", "text/html;charset=utf-8"}),
                None,
            )
            rich_html = clipboard_read(rich_target) if rich_target else ""
            links = extract_links(rich_html, captured_url.canonical_url, expected.forum_id)
            links_by_url = {link.url: link for link in links}
            for parsed in [
                parse_openreview_url(expected.canonical_forum_url),
                parse_openreview_url(captured_url.canonical_url),
                *requested_urls,
            ]:
                links_by_url.setdefault(
                    parsed.canonical_url,
                    CapturedLink("", parsed.canonical_url, parsed.forum_id, parsed.note_id),
                )
            links = list(links_by_url.values())
            checks = validate_page_text(page_text, expected, links)

            payload = {
                "schema_version": 1,
                "requested_url": expected.canonical_url,
                "captured_url": captured_url.canonical_url,
                "canonical_forum_url": expected.canonical_forum_url,
                "forum_id": expected.forum_id,
                "selected_note_id": expected.note_id,
                "captured_at": datetime.now(timezone.utc).isoformat(),
                "window": asdict(target) | {"window_id": target.hex_id},
                "page_text": page_text,
                "links": [asdict(link) for link in links],
                "clipboard_targets": targets,
                "capture_checks": checks,
            }
            write_private_json(Path(args.output), payload)
            print(f"Captured {checks['characters']} characters to {Path(args.output).resolve()}")
            print(f"Found {checks['note_links']} linked note IDs in the rendered page")
    finally:
        try:
            clipboard_write(previous_clipboard)
        except Exception:
            print("warning: could not restore the previous plain-text clipboard", file=sys.stderr)


def manual_bundle(args: argparse.Namespace) -> None:
    source = parse_openreview_url(args.source_url)
    text_path = Path(args.text_file).expanduser().resolve()
    try:
        page_text = text_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CaptureError(f"could not read text file: {exc}") from exc

    links: dict[str, CapturedLink] = {}
    for raw in [source.canonical_forum_url, source.canonical_url, *args.note_url]:
        parsed = parse_openreview_url(raw)
        if parsed.forum_id != source.forum_id:
            raise CaptureError(f"note URL belongs to another forum: {raw}")
        links.setdefault(
            parsed.canonical_url,
            CapturedLink("", parsed.canonical_url, parsed.forum_id, parsed.note_id),
        )
    checks = validate_page_text(page_text, source, links.values())
    payload = {
        "schema_version": 1,
        "requested_url": source.canonical_url,
        "captured_url": source.canonical_url,
        "canonical_forum_url": source.canonical_forum_url,
        "forum_id": source.forum_id,
        "selected_note_id": source.note_id,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "window": None,
        "page_text": page_text,
        "links": [asdict(link) for link in links.values()],
        "clipboard_targets": [],
        "capture_checks": checks | {"manual_fallback": True},
    }
    write_private_json(Path(args.output), payload)
    print(f"Created private manual capture bundle: {Path(args.output).resolve()}")


def launch(args: argparse.Namespace) -> None:
    parsed = parse_openreview_url(args.url)
    chrome = find_chrome()
    environment = os.environ.copy()
    command = [chrome, "--new-window", parsed.canonical_url]
    with open(os.devnull, "wb") as sink:
        subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=sink,
            stderr=sink,
            start_new_session=True,
            env=environment,
        )
    print(f"Opened interactive Chrome: {parsed.canonical_url}")
    print("Complete OpenReview verification/login, expand the full discussion, then confirm the page is ready.")


def list_windows(_: argparse.Namespace) -> None:
    with X11Controller() as controller:
        windows = controller.windows()
    if not windows:
        print("No visible Linux Chrome OpenReview windows found.")
        return
    for window in windows:
        pid = str(window.pid) if window.pid is not None else "?"
        print(f"{window.hex_id}\tpid={pid}\t{window.width}x{window.height}\t{window.title}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    launch_parser = subparsers.add_parser("launch", help="open an OpenReview URL in interactive Chrome")
    launch_parser.add_argument("url")
    launch_parser.set_defaults(func=launch)

    windows_parser = subparsers.add_parser("windows", help="list visible OpenReview Chrome windows")
    windows_parser.set_defaults(func=list_windows)

    capture_parser = subparsers.add_parser("capture", help="capture the authenticated rendered forum")
    capture_parser.add_argument("--expected-url", required=True)
    capture_parser.add_argument("--output", required=True)
    capture_parser.add_argument("--window-id")
    capture_parser.add_argument(
        "--note-url",
        action="append",
        default=[],
        help="additional requested note URL from the same forum; repeat as needed",
    )
    capture_parser.add_argument("--focus-delay", type=float, default=0.45)
    capture_parser.add_argument("--copy-delay", type=float, default=0.65)
    capture_parser.set_defaults(func=capture_authenticated)

    manual_parser = subparsers.add_parser("manual", help="create a capture bundle from a complete text copy")
    manual_parser.add_argument("--source-url", required=True)
    manual_parser.add_argument("--text-file", required=True)
    manual_parser.add_argument("--note-url", action="append", default=[])
    manual_parser.add_argument("--output", required=True)
    manual_parser.set_defaults(func=manual_bundle)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if getattr(args, "focus_delay", 0) < 0 or getattr(args, "copy_delay", 0) < 0:
        parser.error("delays must be non-negative")
    try:
        args.func(args)
    except FileExistsError:
        print(f"error: output already exists: {getattr(args, 'output', '')}", file=sys.stderr)
        return 2
    except (CaptureError, subprocess.SubprocessError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
