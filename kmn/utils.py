import time
from typing import List


def plural(**word):
    word, value = next(iter(word.items()))
    return f'{value} {word}' if value == 1 else f'{value} {word}s'


class Timer:
    def __init__(self):
        self.start: float = None
        self.end: float = None

    def __enter__(self):
        self.start = time.monotonic()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end = time.monotonic()

    def __str__(self):
        return f'{(self.end - self.start) * 1000:.2f}ms'


class Table:
    """
    A class used to format strings into a table.

    From Mousey: https://git.io/vdzzQ
    """

    def __init__(self, *column_titles: str):
        self._rows = [column_titles]
        self._widths = []

        for index, entry in enumerate(column_titles):
            self._widths.append(len(entry))

    def _update_widths(self, row: tuple):
        for index, entry in enumerate(row):
            width = len(entry)
            if width > self._widths[index]:
                self._widths[index] = width

    def add_row(self, *row: str):
        """
        Add a row to the table.
        .. note :: There's no check for the number of items entered, this may cause issues rendering if not correct.
        """
        self._rows.append(row)
        self._update_widths(row)

    def add_rows(self, *rows: List[str]):
        for row in rows:
            self.add_row(*row)

    def _render(self):
        def draw_row(row_):
            columns = []

            for index, field in enumerate(row_):
                # digits get aligned to the right
                if field.isdigit():
                    columns.append(f" {field:>{self._widths[index]}} ")
                    continue

                # regular text gets aligned to the left
                columns.append(f" {field:<{self._widths[index]}} ")

            return "|".join(columns)

        # column title is centered in the middle of each field
        title_row = "|".join(f" {field:^{self._widths[index]}} " for index, field in enumerate(self._rows[0]))
        separator_row = "+".join("-" * (width + 2) for width in self._widths)

        drawn = [title_row, separator_row]
        # remove the title row from the rows
        self._rows = self._rows[1:]

        for row in self._rows:
            row = draw_row(row)
            drawn.append(row)

        return "\n".join(drawn)

    @property
    def rendered(self):
        return self._render()
