from datetime import datetime, time, timedelta
import pytz
from typing import Dict, Any

IST = pytz.timezone('Asia/Kolkata')

# Official NSE Trading Holidays (Equities & F&O)
NSE_HOLIDAYS_2026 = {
    "2026-01-26": "Republic Day",
    "2026-02-18": "Mahashivratri",
    "2026-03-06": "Holi",
    "2026-03-20": "Id-Ul-Fitr (Ramzan Eid)",
    "2026-04-03": "Good Friday",
    "2026-04-14": "Dr. Baba Saheb Ambedkar Jayanti",
    "2026-05-01": "Maharashtra Day",
    "2026-05-27": "Bakri Id / Eid ul-Adha",
    "2026-06-26": "Muharram",
    "2026-08-15": "Independence Day",
    "2026-09-04": "Milad-un-Nabi",
    "2026-10-02": "Mahatma Gandhi Jayanti",
    "2026-10-20": "Dussehra",
    "2026-11-08": "Diwali Laxmi Pujan (Muhurat Trading)",
    "2026-11-10": "Diwali Balipratipada",
    "2026-11-24": "Guru Nanak Jayanti",
    "2026-12-25": "Christmas"
}

class IndianMarketCalendar:
    def __init__(self):
        self.pre_market_open = time(9, 0)
        self.pre_market_close = time(9, 8)
        self.market_open = time(9, 15)
        self.market_close = time(15, 30)
        self.post_market_close = time(16, 0)

    def get_current_ist_time(self) -> datetime:
        return datetime.now(IST)

    def get_market_status(self) -> Dict[str, Any]:
        """
        Evaluates real-time NSE/BSE market status, holiday schedule, and countdown to next session.
        """
        now_ist = self.get_current_ist_time()
        current_date_str = now_ist.strftime("%Y-%m-%d")
        current_time = now_ist.time()
        weekday = now_ist.weekday() # 0 = Monday, 5 = Saturday, 6 = Sunday

        is_weekend = weekday in [5, 6]
        is_holiday = current_date_str in NSE_HOLIDAYS_2026
        holiday_name = NSE_HOLIDAYS_2026.get(current_date_str, None)

        is_pre_market = False
        is_live_market = False
        is_post_market = False
        status_label = "CLOSED"
        reason = "After Hours"

        if is_weekend:
            status_label = "CLOSED (WEEKEND)"
            reason = "Saturday / Sunday Weekly Off"
        elif is_holiday:
            status_label = f"CLOSED (HOLIDAY: {holiday_name})"
            reason = f"NSE Official Holiday: {holiday_name}"
        else:
            if self.pre_market_open <= current_time < self.pre_market_close:
                is_pre_market = True
                status_label = "PRE-MARKET (ORDER DISCOVERY)"
                reason = "Pre-open price discovery session"
            elif self.market_open <= current_time <= self.market_close:
                is_live_market = True
                status_label = "LIVE TRADING OPEN"
                reason = "Regular live trading session (NSE/BSE)"
            elif self.market_close < current_time <= self.post_market_close:
                is_post_market = True
                status_label = "POST-MARKET CLOSING"
                reason = "Closing price settlement session"
            else:
                status_label = "CLOSED (AFTER HOURS)"
                reason = "Outside trading hours (09:15 AM - 03:30 PM IST)"

        # Calculate next market open timestamp
        next_open_dt = self._calculate_next_market_open(now_ist)
        time_until_open = next_open_dt - now_ist
        
        days, remainder = divmod(int(time_until_open.total_seconds()), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        countdown_str = f"{days}d {hours}h {minutes}m {seconds}s" if days > 0 else f"{hours}h {minutes}m {seconds}s"

        # Format next open day label
        days_diff = (next_open_dt.date() - now_ist.date()).days
        if days_diff == 0:
            next_day_prefix = "Today"
        elif days_diff == 1:
            next_day_prefix = "Tomorrow (" + next_open_dt.strftime("%a") + ")"
        else:
            next_day_prefix = next_open_dt.strftime("%a (%b %d)")

        next_open_formatted = f"{next_day_prefix} 09:15 AM IST"

        return {
            "is_live_market": is_live_market,
            "is_pre_market": is_pre_market,
            "is_post_market": is_post_market,
            "is_weekend": is_weekend,
            "is_holiday": is_holiday,
            "holiday_name": holiday_name,
            "status_label": status_label,
            "reason": reason,
            "current_time_ist": now_ist.strftime("%Y-%m-%d %H:%M:%S IST"),
            "next_market_open_ist": next_open_dt.strftime("%Y-%m-%d %H:%M:%S IST"),
            "next_open_formatted": next_open_formatted,
            "countdown_to_open": countdown_str,
            "exchange": "National Stock Exchange of India (NSE)",
            "trading_hours": "09:15 AM - 03:30 PM IST"
        }

    def _calculate_next_market_open(self, now_ist: datetime) -> datetime:
        candidate_date = now_ist.date()
        
        # If today is a weekday and before 9:15 AM, next open is today at 9:15 AM
        if now_ist.weekday() < 5 and now_ist.time() < self.market_open and candidate_date.strftime("%Y-%m-%d") not in NSE_HOLIDAYS_2026:
            return IST.localize(datetime.combine(candidate_date, self.market_open))

        # Otherwise, check tomorrow onwards
        while True:
            candidate_date += timedelta(days=1)
            date_str = candidate_date.strftime("%Y-%m-%d")
            # If not weekend and not holiday, we found next open day!
            if candidate_date.weekday() < 5 and date_str not in NSE_HOLIDAYS_2026:
                return IST.localize(datetime.combine(candidate_date, self.market_open))

market_calendar = IndianMarketCalendar()
