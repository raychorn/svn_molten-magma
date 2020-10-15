require "#{RAILS_ROOT}/vendor/plugins/exception_notification/lib/exception_notifiable"
require 'rubygems'
require 'activesalesforce'

module  ActionController
  module Caching
    module Fragments
      # Name can take one of three forms:
      # * String: This would normally take the form of a path like "pages/45/notes"
      # * Hash: Is treated as an implicit call to url_for, like { :controller => "pages", :action => "notes", :id => 45 }
      # * Regexp: Will destroy all the matched fragments, example: %r{pages/\d*/notes} Ensure you do not specify start and finish in the regex (^$) because the actual filename matched looks like ./cache/filename/path.cache
      def expire_fragment(name, options = nil)
        return if RAILS_ENV == 'test'
        # return unless perform_caching

        key = fragment_cache_key(name)

        if key.is_a?(Regexp)
          # self.class.benchmark "Expired fragments matching: #{key.source}" do
            fragment_cache_store.delete_matched(key, options)
          # end
        else
          # self.class.benchmark "Expired fragment: #{key}" do
          p 'key'
          p key
          p options
            fragment_cache_store.delete(key, options)
          # end
        end
      end
    end
  end
end

module  CacheBuilder
  # requires 'drb'
  DRb.start_service
  drbCacheBuilder = DRbObject.new(nil, 'druby://localhost:9000')

  # Expires the specified fragment and sends a request to the CacheBuilder DRb Server to rebuild the cache fragment. 
  def expire_and_refresh_fragment(name, options = nil)
    expire_fragment(name, options)
    # if in development mode, don't refresh...WEBrick can only handle single requests. 
    # Net::HTTP.get_print( URI.parse(url_for( name )) )
    drbCacheBuilder.expire( url_for(name) )
  end
    
  # Sends a request to the CachingController with corresponding action name. 
  # This action should correspond to a view that loads up all fragments that need to be cached for the _model_.
  def refresh_fragments_for_model(model)
    p "[#{Time.now}] Refreshing cache for Class [#{model.class}]"
    # p Net::HTTP.get_print( URI.parse( url_for( :controller => 'caching', :action => model.class.to_s.underscore, :id => model.id ) ) )
    drbCacheBuilder.expire( url_for( :controller => 'caching', :action => model.class.to_s.underscore, :id => model.id ) )
  end
  
  # Requests the page so the cache can be refreshed.
  def refresh_page(url,current_contact = Sfcontact.find_by_email('derek.haynes@highgroove.com'))
    return if RAILS_ENV == 'test'
    p "[#{Time.now}] Refreshing cache for url [#{url}] and contact [#{current_contact.email}]"
    p URI.parse(  url_for( url.merge({:cache_key => AppConstants::CACHE_KEY, :cached_contact_id => current_contact.id}) ) )
    # Net::HTTP.get_print( URI.parse(  url_for( url.merge({:cache_key => AppConstants::CACHE_KEY, :cached_contact_id => current_contact.id}) ) ) )
    drbCacheBuilder.expire( url_for( url.merge({:cache_key => AppConstants::CACHE_KEY, :cached_contact_id => current_contact.id}) ) )
  rescue => e
    p "Error occured refreshing cache: #{e}"
  end
end

class CacheCleanerObserver < ActiveRecord::Observer
  include ActionController::Caching::Fragments
  ActionController::Base.fragment_cache_store = :file_store, "#{RAILS_ROOT}/tmp/cache"
  include CacheBuilder
  include ActionController::UrlWriter
  
  default_url_options[:host] = RAILS_ENV == 'production' ? 'molten.moltenmagma.com' : 'localhost:3000'
  
  def self.reloadable?; false; end
  
  
end