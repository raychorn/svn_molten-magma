class AddSearchRegexAppSetting < ActiveRecord::Migration
  def self.up
    AppSetting.create!(:name => "Solutions Search RegEx",
                      :value => "/\"*\"/",
                      :field_type => 'text_field')
  end

  def self.down
    AppSetting.find_by_name("Solutions Search RegEx").destroy
  rescue
  end
end
