class AdjustCase < ActiveRecord::Migration

  def self.up
    change_column :sfcase, :case_number, :integer
  end

  def self.down
    change_column :sfcase, :case_number, :string
  end

end