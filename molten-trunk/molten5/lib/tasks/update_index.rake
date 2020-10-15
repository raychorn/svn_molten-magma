namespace :search do

  desc "Builds the search index." 
  task :build_index => :environment do
    `#{RAILS_ROOT}/script/runner 'Sfsolution.rebuild_index'`
    `#{RAILS_ROOT}/script/runner 'Sfcase.rebuild_index'`
  end

end