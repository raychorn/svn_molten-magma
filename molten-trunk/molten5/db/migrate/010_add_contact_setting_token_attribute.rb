class AddContactSettingTokenAttribute < ActiveRecord::Migration
  def self.up
    add_column :sfcontact_setting, :token, :string
  end

  def self.down
    remove_column :sfcontact_setting, :token
  end
end
