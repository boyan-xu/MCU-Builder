"""A local software example only, with no device or shell access."""
def lamp_request(request):
    return request != 0

assert lamp_request(1)
assert not lamp_request(0)
print('PASS: fictional host behavior; physical lamp not tested')
