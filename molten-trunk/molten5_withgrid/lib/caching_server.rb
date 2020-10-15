require 'drb'
require 'net/http'

class CacheBuilder
  def expire(url)
    # spawn thread to expire url here
    Thread.new(url) do
      # Net::HTTP.get_print( URI.parse(url_for( name )) )
      puts "Expiring: #{url}"

      begin 
        sleep 5 # simulating a long http get
        Net::HTTP.get_print( URI.parse(url) )
        puts "Expired: #{url}"
      
      rescue Exception => e
        puts "Exception: #{e.to_s}"
      end
    end # end Thread
  end
end

svrObjCacheBuilder = CacheBuilder.new
DRb.start_service('druby://localhost:9000', svrObjCacheBuilder)
DRb.thread.join