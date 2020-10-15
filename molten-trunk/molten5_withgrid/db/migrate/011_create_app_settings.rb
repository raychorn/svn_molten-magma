class CreateAppSettings < ActiveRecord::Migration
  def self.up
    create_table :app_setting do |t|
      t.column :name, :string
      t.column :value, :string
      t.column :description, :text
      t.column :updated_at, :datetime
    end
  end

  def self.down
    drop_table :app_setting
  end
end
