# Lots of failure w/this!
# test_show(SolutionsControllerTest):
# SystemStackError: stack level too deep
#     /Users/itsderek23/Projects/molten/vendor/plugins/paginating_find/lib/paginating_find.rb:103:in `find_without_pagination'
#     /Users/itsderek23/Projects/molten/vendor/plugins/paginating_find/lib/paginating_find.rb:103:in `find'
#     /Users/itsderek23/Projects/molten/vendor/rails/activerecord/lib/active_record/fixtures.rb:806:in `find'
#     /Users/itsderek23/Projects/molten/vendor/rails/activerecord/lib/active_record/fixtures.rb:892:in `sfcontact'
#     /Users/itsderek23/Projects/molten/vendor/rails/activerecord/lib/active_record/fixtures.rb:888:in `sfcontact'
#     ./test/functional/admin/contacts_controller_test.rb:16:in `setup_without_fixtures'
#     /Users/itsderek23/Projects/molten/vendor/rails/activerecord/lib/active_record/fixtures.rb:979:in `full_setup'

# ActiveRecord::Base.send(:include, PaginatingFind)
# ActionView::Base.send(:include, PaginatingFind::Helpers)