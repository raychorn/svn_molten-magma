class CreateSolutionRelevancyRecord < ActiveRecord::Migration
  def self.up
    SolutionRelevancy.create!(
      :id => 1,
      :rating_value_one => 25,
      :rating_value_two => 60,
      :rating_value_three => 90,
      :rating_value_four => 100,
      :view_value => 50,
      :update_value => 100
    )
  end

  def self.down
    SolutionRelevancy.destroy_all
  end
end
