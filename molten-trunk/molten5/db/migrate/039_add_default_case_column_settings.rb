class AddDefaultCaseColumnSettings < ActiveRecord::Migration
  def self.up
    SfcontactSetting.find(:all).each do |c|
      c.send(:initialize_case_columns_setting)
    end
  end

  def self.down
  end
end
