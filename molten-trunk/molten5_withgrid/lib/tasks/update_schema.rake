namespace :salesforce do

  desc "Propagates SalesForce schema changes to the local database." 
  task :update_schema => :environment do
    `#{RAILS_ROOT}/script/runner 'SalesforceSync.update_schema'`
  end

end