class RefreshCache < ActiveRecord::Base
  belongs_to :refreshable, :polymorphic => true
  set_primary_key "id"
  
  # Calls #refresh_cache on every refreshable item.
  # Requires that an observer exist for the refreshable item (ie Sfcase => SfcaseObserver).
  # Items are refreshed starting with the most recent records. After the refresh is complete, the 
  # entry in the RefreshCache table is destroyed.
  def self.refresh_all
    find(:all, :order => "created_at DESC").map { |r| r.refreshable  }.compact.each do |refreshable|
      begin
        RefreshCache.transaction do 
          "#{refreshable.class}Observer".constantize.instance.send(:refresh_cache, refreshable)
          destroy_all "refreshable_type = '#{refreshable.class}' AND refreshable_id = '#{refreshable.id}'"
        end
      rescue => e
        logger.info("Failed to update [#{refreshable.class} / #{refreshable.id}]: #{e} ")
        logger.info(e.backtrace)
      end
    end
  end
end
