from textual.app import App
from textual.containers import Grid
from textual.widgets import Button, Static

import random


VARIANTS = ["default", "primary", "success", "warning", "error"]

class GridLayoutApp(App):
    def compose(self):
        grid = Grid()
        grid.styles.grid_size_rows = rows = 6
        grid.styles.grid_size_columns = cols = 4
        with grid:
            for row in range(rows):
                for col in range(cols):
                    button = Button(f"Button ({row=}, {col=})", variant=random.choice(VARIANTS))
                    button.styles.border = ("solid", "green")
                    button.styles.width = "1fr"
                    button.styles.height = "1fr"
                    yield button
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        button = event.button
        current_variant = button.variant
        next_variant = VARIANTS[(VARIANTS.index(current_variant) + 1) % len(VARIANTS)]
        button.variant = next_variant
        self.notify(f"\"{event.button.label}\" pressed!", severity="info")

if __name__ == "__main__":
    app = GridLayoutApp()
    app.run()
