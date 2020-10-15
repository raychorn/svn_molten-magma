# require 'rubygems'
ActiveRecord::Base.pluralize_table_names=false
require_dependency 'app_constants'
require_dependency 'salesforce_record'
require_dependency 'salesforce_helper'
require_dependency 'pagination'
require_dependency 'cachable'
require_dependency 'solution_viewing'
require 'enumerator'
require 'acts_as_tree_mods'
require 'odd_even'
require_dependency 'acts_as_viewable'
ActiveRecord::Base.send(:include, ActiveRecord::Acts::Viewable)
require_dependency 'acts_as_syncable'
ActiveRecord::Base.send(:include, ActiveRecord::Acts::Syncable)
require 'watcher_classes'

require 'product_team_classes'
require 'multiple_db_migrations'

# require "#{RAILS_ROOT}/vendor/activesalesforce-1.1.6/lib/asf_adapter.rb"


ExceptionNotifier.exception_recipients = %W(derek.haynes@highgroove.com #{AppConstants::SUPPORT_EMAIL})
ExceptionNotifier.email_prefix = "[MOLTEN] "
ExceptionNotifier.sender_address = %("Application Error" <molten_error@molten-magma.com>)

Rails::Initializer.run do |config|
  
end

ActiveRecord::Base.lock_optimistically = false

Inflector.inflections do |inflect| 
  inflect.uncountable 'data'
  inflect.irregular 'data', 'data'
end

#class NilClass
#  def split
#    return nil
#  end
#end

