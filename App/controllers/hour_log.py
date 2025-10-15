from App.models.hour_log import HourLog


def get_log (log_id):
    return HourLog.query.get(log_id)
