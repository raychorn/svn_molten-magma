module FerretMixin
  module Acts #:nodoc:
    module ARFerret #:nodoc:

      # decorator that adds a total_hits accessor to search result arrays
      class SearchResults
      
        # Changed to db/ferret_index
        def self.init_index_basedir
          index_base = "#{RAILS_ROOT}/db/ferret_index"
          ensure_directory index_base
          @@index_dir = "#{index_base}/#{RAILS_ENV}"
          ensure_directory @@index_dir
        end
      
        def self.append_features(base)
          super
          base.extend(ClassMethods)
        end
      
      end

      
      
    end
  end
end