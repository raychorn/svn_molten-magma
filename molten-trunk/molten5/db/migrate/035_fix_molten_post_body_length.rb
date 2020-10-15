class FixMoltenPostBodyLength < ActiveRecord::Migration
  def self.up
    change_column :sfmolten_post, :body__c, :text
  end

  def self.down
    change_column :sfmolten_post, :body__c, :string
  end
end
