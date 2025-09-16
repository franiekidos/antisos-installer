import subprocess
import json
from textual.widgets import Static, RadioSet, RadioButton, Button
from textual.containers import Vertical, Horizontal
from textual.app import ComposeResult

def get_block_devices():
    try:
        out = subprocess.run(
            ["lsblk", "-o", "NAME,SIZE,MODEL,TYPE", "-J"],
            capture_output=True, text=True, check=True
        )
        return json.loads(out.stdout).get("blockdevices", [])
    except Exception as e:
        return [{"name": "error", "size": "0", "model": str(e), "type": "disk"}]

class SelectDiskPage(Vertical):
    """Disk selection page."""

    def compose(self) -> ComposeResult:
        yield Static("Select target disk", id="part-title")
        self.disk_radio = RadioSet(id="disk-radio")
        for dev in get_block_devices():
            if dev["type"] == "disk":
                label = f"/dev/{dev['name']} ({dev['size']} {dev.get('model','')})"
                self.disk_radio.mount(RadioButton(label))
        yield self.disk_radio

        with Horizontal():
            yield Button("Back", id="disk-back")
            yield Button("Advanced (GParted)", id="disk-advanced")
            yield Button("Next", id="disk-next")

    @staticmethod
    def launch_gparted():
        subprocess.run(["sudo", "gparted"])