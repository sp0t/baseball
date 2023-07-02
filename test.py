

from schedule import schedule


rosters = schedule.get_rosters(717548)
# print(rosters['position']['away'], rosters['position']['home'], rosters['pitcher']['away'], rosters['pitcher']['home'])
for el in rosters['position']['away']:
    print(el, rosters['position']['away'][el], type(rosters['position']['away'][el]))
for el in rosters['position']['home']:
    print(el, rosters['position']['home'][el])
for el in rosters['pitcher']['away']:
    print(el, type(el))
for el in rosters['pitcher']['home']:
    print(el)