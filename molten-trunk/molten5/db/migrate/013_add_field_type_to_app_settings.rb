class AddFieldTypeToAppSettings < ActiveRecord::Migration
  def self.up
    add_column :app_setting, :field_type, :string, :default => "text_field"
  end

  def self.down
    remove_column :app_setting, :field_type
  end
end
