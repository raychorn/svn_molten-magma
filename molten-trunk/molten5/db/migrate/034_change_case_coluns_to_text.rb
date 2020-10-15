class ChangeCaseColunsToText < ActiveRecord::Migration
  
  COLS = [:design_geometryn_m__c, :speed_m_hz__c, :cell_count_k_objects__c]
  
  def self.up
    COLS.each { |col| change_column :sfcase, col, :string }
  end

  def self.down
    COLS.each { |col| change_column :sfcase, col, :integer }
  end
end
