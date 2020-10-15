module  Cachable
  # Expires the cache for the specified _model_ by opening an HTTP connection to the Cache Controller. 
  # The URI specified by _AppConstants::CACHE_URI_ will be appended with the underscored name of the model. 
  # IE:
  # Sfcase => posts to: http://localhost:3000/caching/sfcase?id=1223344
  # This should be placed in an _#after_save_ callback.
  # def expire_cache(model)
 #    return if RAILS_ENV=="test"
 #    begin
 #      logger.info "Opening connnection to #{AppConstants::CACHE_URI}#{model.class.to_s.underscore}"
 #      logger.info Net::HTTP.post_form(URI.parse(AppConstants::CACHE_URI+"#{model.class.to_s.underscore}"),{:id => model.id}).body
 #    rescue
 #      logger.info "An error occurred trying to connect to the caching controller to expire [#{model.class} / #{model.id}]"
 #    end
 #  end
end