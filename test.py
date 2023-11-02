import statsapi as mlb
from schedule import schedule

today_schedule = schedule.get_schedule_from_mlb()     
print(today_schedule)