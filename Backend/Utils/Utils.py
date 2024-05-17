from datetime import datetime, timedelta

from datetime import datetime


class Utils:
    @staticmethod
    def time_left_until(unix_timestamp):
        current_time = datetime.utcnow()
        target_time = datetime.utcfromtimestamp(unix_timestamp)
        time_difference = target_time - current_time

        if time_difference < timedelta(0):
            return 'Time is up'

        days = time_difference.days
        hours, remainder = divmod(time_difference.seconds, 3600)
        minutes = remainder // 60

        if days > 0:
            return f'{days} days'
        else:
            return f'{hours}H : {minutes}m'

    @staticmethod
    def unix_to_global_time(unix_timestamp):
        # Convert the Unix timestamp to a datetime object
        dt_object = datetime.utcfromtimestamp(unix_timestamp)
        # Format the datetime object to a string including the day, date, and time
        formatted_time = dt_object.strftime('%A %d/%m %H:%M UTC')
        return formatted_time

    @staticmethod
    def get_utc_date(days_time_delta=0):
        utc_now = datetime.utcnow()

        # If days_time_delta is 1, then it means yesterday (so, we subtract 1 day).
        # If days_time_delta is -1, then it means tomorrow (so, we add 1 day).
        # Therefore, we negate the value of days_time_delta to get the required behavior.
        adjusted_date = utc_now - timedelta(days=-days_time_delta)
        return adjusted_date.strftime("%Y%m%d")

    @staticmethod
    def convert_to_human_date(timestamp):
        human_date = datetime.fromtimestamp(timestamp).strftime('%A, %B %d, %Y %I:%M:%S %p')
        return human_date
