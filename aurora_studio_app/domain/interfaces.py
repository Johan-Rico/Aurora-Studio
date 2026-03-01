from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, time
from decimal import Decimal


class NotificationSender(ABC):
	@abstractmethod
	def send_booking_confirmation(
		self,
		*,
		to_email: str,
		customer_name: str,
		reservation_code: str,
		booking_date: date,
		start_time: time,
		end_time: time,
		service_names: list[str],
		total_price: Decimal,
	) -> None:
		raise NotImplementedError


class ReservationCodeGenerator(ABC):
	@abstractmethod
	def generate(self) -> str:
		raise NotImplementedError

