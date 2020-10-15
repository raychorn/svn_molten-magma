# THIS IS NOT IN USE - NO LONGER CACHING THE SHOW VIEW
class SfattachObserver < CacheCleanerObserver
  def after_save(sfattach)
    # expire solutions#show fragments
    expire_fragment(:controller => 'solutions', :action => 'show', :part => 'solution_detail', :id => sfattach.parent.id )
    
    RefreshCache.create!(:refreshable => sfattach, :refreshable_type => 'Sfattach')
  rescue
  end
  
  def refresh_cache(sfattach)
    refresh_page({:controller => 'solutions', :action => 'show', :id => sfattach.parent.id}, Sfcontact.find(:first))
  rescue
  end
end