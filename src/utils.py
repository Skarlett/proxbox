
def percentage(part, whole):
  try:
    return 100 * float(part) / float(whole)
  except ZeroDivisionError:
    return 0

def h_time(seconds):
  m, s = divmod(float(seconds), 60)
  h, m = divmod(m, 60)
  return "%d:%02d:%02d" % (h, m, s)

