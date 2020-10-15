class AddSolutionUpdateRating < ActiveRecord::Migration
  def self.up
    add_column :solution_relevancy, :update_value, :integer
  end

  def self.down
    remove_column :solution_relevancy, :update_value
  end
end
