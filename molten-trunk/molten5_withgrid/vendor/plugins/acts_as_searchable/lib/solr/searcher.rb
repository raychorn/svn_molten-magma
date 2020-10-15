require("open-uri")
require("rexml/document")

module MojoDNA::Searchable::Solr
  class Searcher
    include REXML
    
    def search(klass, query, options = {})
      ::MojoDNA::Searchable::Solr::Searcher.search(klass, query, options)
    end
    
    # if :load is set to false, an array of model ids will be returned rather than an array of objects
    # set :offset to the initial offset in the resultset
    # set :limit to the number of desired results returned from the resultset
    # Ferret provides these, but does not provide metadata about the total number of results
    # set :sort_by to the fields that the results should be sorted by (in order).  Alternately, pass a Ferret::Search::Sort
    # set :reverse to true if you'd like the results in reverse order (only if a sorted field is provided)
    # TODO support paginator (pagination_helper.rb:find_collection_for_pagination would need to be overwritten to not only use find_all)
    #   conditions (option), order_by (option), paginator
    #     paginator.items_per_page paginator.current.offset
    # TODO returned stored fields as part of ResultSet
    # set :default_fields to be an array of fields that should be used as default fields
    def self.search(klass, query, options = {})
      options = { :load => true, :offset => 0, :limit => ::Searchable::MAX_RESULTS, :sort_by => nil, :reverse => false, :default_field => nil, :default_fields => [] }.update( options ) if options.is_a?(Hash)

      logger = klass.logger

      query = "+_type:#{klass.to_s} #{query}"

      # TODO sorting
      # TODO cheap QueryParsing

      doc = Document.new(open("http://localhost:8983/solr/select/?q=#{ERB::Util.url_encode(query)}&version=2.1&start=#{options[:offset]}&rows=#{options[:limit]}&indent=on"))
      results = []
      results.num_results = XPath.match(doc, "//result/@numFound").map(&:value).first
      results.offset = options[:offset]
      
      XPath.match(doc, "//doc/str[contains(@name,'_type-id')]/text()").map(&:value).each do |r|
        type, id = r.split("-")
        results << [type, id.to_i]
      end
      
      if options[:load]
        # load all results if specified
        
        # handle resultsets with multiple returned types
        klasses = {}
        results.each do |r|
          type, id = r
          type = type.constantize
          id.score = r.score if r.respond_to?(:score)
          klasses[type] ||= []
          klasses[type] << id
        end
      
        # reset the results and load everything
        results = []
        klasses.each do |k, v|
          class_results = k.find( v )
          class_results.each do |r|
            v.each do |id|
              r.score = id.score if r.id == id and r.respond_to?(:score)
            end
          end
          results += class_results
        end
        
        # re-sort the results by score to intermingle result types
        # TODO figure out how to do this with the absence of a score
        # results.sort! {|x,y| y.score <=> x.score }
      end
      

      return results
      
      if query.is_a?(::Ferret::Search::Query)
        searcher = searcher(klass)
        # TODO QueryFilters are buggy
        # @filter = Ferret::QueryFilter.new( Ferret::Search::TermQuery.new( Ferret::Index::Term.new("_type", klass.to_s ) ) )
        bq = ::Ferret::Search::BooleanQuery.new
        bq.add_query(query, ::Ferret::Search::BooleanClause::Occur::MUST) 
        bq.add_query( ::Ferret::Search::TermQuery.new( ::Ferret::Index::Term.new("_type", klass.to_s ) ) )
        query = bq

        if options[:sort_by].is_a?(::Ferret::Search::Sort)
          sort = options[:sort_by]
        else
          sort_fields = []
          unless options[:sort_by].nil?
            if options[:sort_by].is_a?(Symbol)
              sort_fields << ::Ferret::Search::SortField.new( options[:sort_by].to_s, :reverse => options[:reverse] )
            else
              sort_fields += options[:sort_by].collect { |f| ::Ferret::Search::SortField.new( "_sort-#{f.to_s}", :reverse => options[:reverse] ) }
            end
          end
          sort_fields += [::Ferret::Search::SortField::FIELD_SCORE, ::Ferret::Search::SortField::FIELD_DOC]
          sort = ::Ferret::Search::Sort.new( sort_fields, options[:reverse] )
        end

      elsif query.respond_to?(:to_s)
        fields = (options[:default_field].to_a + options[:default_fields].to_a).collect{|f| f.to_s }
        if fields.empty?
          fields = klass.default_fields
        end

        # TODO allow overriding of default AND/OR behavior
        query_parser = ::Ferret::QueryParser.new(fields, :analyzer => analyzer, :occur_default => ::Ferret::Search::BooleanClause::Occur::MUST)
        results = search( klass, query_parser.parse( query.to_s ), options )
      end

      results
    end
  end
end