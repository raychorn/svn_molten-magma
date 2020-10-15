class ConvertDesignGeometryToInteger < ActiveRecord::Migration
  def self.up
    change_column :sfcase, :design_geometryn_m__c, :integer
  end

  def self.down
    change_column :sfcase, :design_geometryn_m__c, :string
  end
end
