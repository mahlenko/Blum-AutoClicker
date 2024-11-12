import os
import asyncio
import time
import random
import math
from itertools import product

import keyboard
import mouse
import pyautogui

from core.clicker.misc import Utilities
from core.logger.logger import logger
from core.localization.localization import get_language
from core.config.config import get_config_value

from typing import Tuple, List, Any


class BlumClicker:
    def __init__(self):
        self.utils = Utilities()

        self.paused: bool = True
        self.window_options: str | None = None
        self.replays: int = 0

    async def handle_input(self) -> bool:
        """
        Handles the input for pausing or starting the clicker.

        :return: whether the input was handled
        """
        if keyboard.is_pressed(get_config_value("START_HOTKEY")) and self.paused:
            self.paused = False
            logger.info(get_language("PRESS_P_TO_PAUSE"))
            await asyncio.sleep(0.2)

        elif keyboard.is_pressed(get_config_value("TOGGLE_HOTKEY")):
            self.paused = not self.paused
            logger.info(
                get_language("PROGRAM_PAUSED")
                if self.paused
                else get_language("PROGRAM_RESUMED")
            )
            await asyncio.sleep(0.2)

        return self.paused

    def find_objects(self, screen: Any, rect: Tuple[int, int, int, int]) -> bool:
        """
        Click on the found freeze.

        :param self:
        :param screen: the screenshot
        :param rect: the rectangle
        :return: whether the image was found
        """
        width, height = screen.size

        use_freezing = get_config_value("USE_FREEZING")

        for x, y in product(range(0, width, 5), range(140, height, 5)):
            r, g, b = screen.getpixel((x, y))

            has_flower = self.detect_color_range((r, g, b), (208, 216, 0))

            if use_freezing:
                has_freeze = self.detect_color_range((r, g, b), (90, 205, 220))
            else:
                has_freeze = False

            if has_flower or has_freeze:
                screen_x = rect[0] + x
                screen_y = rect[1] + y
                mouse.move(screen_x, screen_y, absolute=True)
                mouse.click(button=mouse.LEFT)
                return True

        return False

    @staticmethod
    def detect_color_range(haystack: Tuple[int, int, int], needle: Tuple[int, int, int], range: int = 15) -> bool:
        return ((needle[0] - range) <= haystack[0] <= (needle[0] + range)
                and (needle[1] - range) <= haystack[1] <= (needle[1] + range)
                and (needle[2] - range) <= haystack[2] <= (needle[2] + range))

    @staticmethod
    def detect_reload_screen(screen: Any) -> bool:
        """
        Reload app.

        :param screen: the screenshot
        :return: whether the reload screen found
        """
        width, height = screen.size

        x1, y1 = (math.ceil(width * 0.43781), math.ceil(height * 0.60252)) 
        x2, y2 = (math.ceil(width * 0.24626), math.ceil(height * 0.429775)) 

        reload_button = screen.getpixel((x1, y1))
        white_pixel = screen.getpixel((x2, y2))

        if reload_button == (40,40,40) and white_pixel == (255,255,255):
            time.sleep(0.5)
            keyboard.press_and_release('F5')
            return True

        return False

    def detect_replay(self, screen: Any, rect: Tuple[int, int, int, int]) -> bool:
        """
        Click on the 'Play (nn left)' button.

        :param screen: the screenshot
        :param rect: the rectangle
        :return: whether the image was found
        """

        max_replays = get_config_value("REPLAYS")
        replay_delay = get_config_value("REPLAY_DELAY")

        screen_x = rect[0] + int(screen.size[0] * 0.3075)
        screen_y = rect[1] + int(screen.size[1] * 0.87)

        if not pyautogui.pixel(screen_x, screen_y) == (255, 255, 255):
            return False

        if self.replays >= max_replays:
            return logger.error(
                get_language("REPLAY_LIMIT_REACHED").format(replays=max_replays)
            )

        delay = random.randint(replay_delay, replay_delay + 3) + random.random()
        logger.debug(
            f"Detected the replay button. Remaining replays: {max_replays - self.replays} // Delay: {delay:.2f}"
        )
        time.sleep(delay)

        mouse.move(
            screen_x + random.randint(1, 10),
            screen_y + random.randint(1, 10),
            absolute=True,
        )
        mouse.click(button=mouse.LEFT)

        time.sleep(1)
        self.replays += 1

        return True

    async def run(self) -> None:
        """
        Runs the clicker.
        """
        try:
            window = self.utils.get_window()
            if not window:
                return logger.error(get_language("WINDOW_NOT_FOUND"))

            logger.info(get_language("CLICKER_INITIALIZED"))
            logger.info(get_language("FOUND_WINDOW").format(window=window.title))
            logger.info(get_language("PRESS_S_TO_START"))

            while True:
                if await self.handle_input():
                    continue

                rect = self.utils.get_rect(window)

                screenshot = self.utils.capture_screenshot(rect)

                # self.collect_green(screenshot, rect)
                # self.collect_freeze(screenshot, rect)
                self.find_objects(screenshot, rect)

                self.detect_replay(screenshot, rect)
                self.detect_reload_screen(screenshot)

        except (Exception, ExceptionGroup) as error:
            logger.error(get_language("WINDOW_CLOSED").format(error=error))
