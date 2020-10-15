class AddRelevancyToSolutionSetting < ActiveRecord::Migration
  def self.up
    add_column :sfsolution_setting, :relevancy, :integer, :default => 50
  end

  def self.down
    remove_column :sfsolution_setting, :relevancy
  end
end
