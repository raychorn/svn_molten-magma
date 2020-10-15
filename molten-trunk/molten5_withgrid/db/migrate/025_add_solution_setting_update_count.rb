class AddSolutionSettingUpdateCount < ActiveRecord::Migration
  def self.up
    add_column :sfsolution_setting, :updates, :integer, :default => 0
  end

  def self.down
    remove_column :sfsolution_setting, :updates
  end
end
