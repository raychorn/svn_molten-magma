class ChangeConfirmationAttributesToDates < ActiveRecord::Migration
  
  CHANGE_TO_DATES = [:portal_last_confirm_date__c, :portal_last_confirm_sent_date__c]
  
  def self.up
    CHANGE_TO_DATES.each do | attr |
      change_column :sfcontact, attr, :datetime
    end
  end

  def self.down
    CHANGE_TO_DATES.each do |attr|
      change_column :sfcontact, attr, :string
    end
  end
end
