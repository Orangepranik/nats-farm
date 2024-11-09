import datetime
current_time = int((datetime.datetime.now()).timestamp())
print(datetime.datetime.fromtimestamp(current_time)+datetime.timedelta(hours=8))