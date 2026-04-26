import os
import sys
import time
from fluent.runtime import FluentBundle, FluentResource
from core.config import config

class LocalizationManager:
    def __init__(self, locales_path: str):
        self.locales_path = locales_path
        self.bundles = {}
        self._load_locales()

    def _load_locales(self):
        for locale in os.listdir(self.locales_path):
            locale_dir = os.path.join(self.locales_path, locale)
            if not os.path.isdir(locale_dir):
                continue
            
            bundle = FluentBundle([locale])
            for filename in os.listdir(locale_dir):
                if filename.endswith(".ftl"):
                    with open(os.path.join(locale_dir, filename), "r", encoding="utf-8") as f:
                        resource = FluentResource(f.read())
                        bundle.add_resource(resource)
            self.bundles[locale] = bundle

    def get_text(self, locale: str, message_id: str, **kwargs) -> str:
        bundle = self.bundles.get(locale) or self.bundles.get(config.default_locale)
        if not bundle:
            return message_id
        
        message = bundle.get_message(message_id)
        if not message or not message.value:
            return message_id
        
        result, errors = bundle.format_pattern(message.value, kwargs)
        return result

# Path to locales directory relative to this file (src/utils/l10n.py -> src/locales)
LOCALES_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "locales")
l10n = LocalizationManager(LOCALES_PATH)
