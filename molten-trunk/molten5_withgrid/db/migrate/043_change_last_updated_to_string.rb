class ChangeLastUpdatedToString < ActiveRecord::Migration
  def self.up
    change_column :sfcase, :last_updated__c, :datetime
  end

  def self.down
    change_column :sfcase, :last_updated__c, :string
  end
end
