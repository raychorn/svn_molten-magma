require File.dirname(__FILE__) + '/../test_helper'

class SfsolutionTest < Test::Unit::TestCase
  fixtures :sfsolution, :viewing, :sfcontact, :sfcatnode, :sfcatdata, :solution_relevancy
  
  def setup
    Sfsolution.find(:all).each { |s| s.update_attribute('status',nil)}
    @solution = sfsolution(:make_a_pizza)
    @derek = sfcontact(:derek)
  end
  
  def test_rate
    # rate a solution w/o a rating
    @solution.rate!('one')
    assert_equal 1, @solution.reload.rating.one
    
    # rate again...make sure it increments
    @solution.rate!('one')
    assert_equal 2, @solution.reload.rating.one
  end
  
  def test_published
    assert !@solution.published?
    @solution.publish!
    assert @solution.published?
  end
  
  def test_set_relevancy
    # no data
    relevancy_before = @solution.relevancy
    @solution.set_relevancy!
    assert_equal @solution.reload.relevancy, relevancy_before
    
    # view a solution
    test_view
    assert @solution.reload.relevancy > 0
    relevancy_before = @solution.relevancy
    
    # rate a solution
    test_rate
    @solution.set_relevancy!
    assert_equal @solution.reload.relevancy, relevancy_before
    relevancy_before = @solution.relevancy
    
    # update a solution
    @solution.save
    @solution.set_relevancy!
    assert @solution.reload.relevancy > relevancy_before
  end
  
  def test_set_relevancies
    assert_equal AppConstants::DEFAULT_SOLUTION_RELEVANCY, @solution.relevancy
    test_set_relevancy
    Sfsolution.set_relevancies
    assert @solution.reload.relevancy > 0
  end
  
  def test_list_ratings
    test_rate
    assert_equal 4, @solution.list_ratings.size
  end
  
  def test_total_votes
    test_rate
    assert_equal 2, @solution.total_votes
  end

  def test_find_new
    # no published solutions
    solutions = Sfsolution.find_new(@derek)
    assert solutions.empty?
    
    # now publish them...
    Sfsolution.update_all("status = '#{Sfsolution::STATUSES[:published]}'")
    
    solutions = Sfsolution.find_new(@derek)
    assert solutions.any?
    assert_equal solutions, solutions.sort { |x,y| y.last_modified_date <=> x.last_modified_date  }
  end
  
  def test_category_tree
    cats = Sfcatnode.find(:all).reject { |cat| cat == sfcatnode(:another_category) }
    category_tree = sfsolution(:fold_clothes).category_tree
    assert_equal cats.size, category_tree.size
    
    category_tree.each do |cat|
      assert cats.include?(cat)
    end
  end
  
  def test_method_missing
    assert_equal @solution.product_name, @solution.product_name__c
  end
  
  def test_view
    Sfsolution.find(:all).each { |s| s.save }
    viewed_solution = Sfsolution.view(@solution.id,@derek)
    assert_equal @solution, viewed_solution
    assert @solution.viewings(true).any?
    assert @derek.viewings(true).any?
    assert_equal 1, @solution.reload.views
  end
  
  def test_find_popular
    test_view
    # no published solutions...
    assert Sfsolution.find_popular.empty?
    
    # now publish
    Sfsolution.update_all("status = '#{Sfsolution::STATUSES[:published]}'")
    assert Sfsolution.find_popular.any?
  end
  
  def test_delegate_views
    assert @solution.respond_to?(:views)
  end
  
  def test_initialize_settings
    SfsolutionSetting.destroy_all
    assert_nil @solution.settings
    @solution.save
    assert @solution.settings
  end
end
