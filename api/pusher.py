import pusher

pusher = pusher.Pusher(
  app_id='1801083',
  key='1c26d2cd463b15a19666',
  secret='e4e61f70e4b17c1a7de8',
  cluster='eu',
  ssl=True
)

pusher_client.trigger('my-channel', 'my-event', {'message': 'hello world'})