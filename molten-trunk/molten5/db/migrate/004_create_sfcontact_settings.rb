class CreateSfcontactSettings < ActiveRecord::Migration
  def self.up
    create_table :sfcontact_setting do |t|
      t.column :sfcontact_id, :string
    end
  end

  def self.down
    drop_table :sfcontact_setting
  end
end
