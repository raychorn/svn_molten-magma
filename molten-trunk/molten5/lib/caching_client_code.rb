require 'drb'

DRb.start_service
drbCacheBuilder = DRbObject.new(nil, 'druby://localhost:9000')

drbCacheBuilder.expire("http://localhost:3000/bob/jones")