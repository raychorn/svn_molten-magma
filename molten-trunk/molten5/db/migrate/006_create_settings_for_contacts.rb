class CreateSettingsForContacts < ActiveRecord::Migration
  def self.up
    Sfcontact.find(:all).each { |c| c.save! }
  end

  def self.down
    SfcontactSetting.destroy_all
  end
end
