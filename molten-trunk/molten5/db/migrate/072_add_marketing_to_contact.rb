class AddMarketingToContact < ActiveRecord::Migration
  def self.up
    add_column :sfcontact, :last_read_marketing_message_id, :string
  end

  def self.down
    remove_column :sfcontact, :last_read_marketing_message_id
  end
end
