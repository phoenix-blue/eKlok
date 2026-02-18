"""Config flow voor Stedin Eklok integratie."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN


class StedinEklokConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle een config flow voor Stedin Eklok."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle de initiële stap."""
        if user_input is not None:
            # Check of er al een entry bestaat
            await self.async_set_unique_id("stedin_eklok")
            self._abort_if_unique_id_configured()
            
            return self.async_create_entry(
                title="Stedin Eklok",
                data={},
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({}),
            description_placeholders={
                "info": "Deze integratie haalt data op van Stedin Eklok om de beste momenten voor energieverbruik te tonen."
            },
        )
