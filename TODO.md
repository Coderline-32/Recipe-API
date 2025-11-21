# Optimization Tasks for Recipe API Performance

## 1. Implement Selective Prefetching in RecipeViewSet
- Modify `get_queryset()` in `recipe/views.py` to prefetch only essential related data for list views
- For list actions: prefetch 'tags' and 'ingredients'
- For retrieve action: add 'images', 'comments', 'versions', 'ratings'

## 2. Add Database Indexes (if needed)
- Review existing indexes in `recipe/models.py`
- Add any missing indexes for common query fields (author, visibility, difficulty, cook_time, etc.)

## 3. Configure Caching for User Recipe Endpoints
- Ensure cache backend is properly configured in `RecipeAPI/settings.py`
- Add caching decorators or cache_page to list views in RecipeViewSet
- Implement cache invalidation strategies

## 4. Optimize Serializers
- Review `recipe/serializers.py` for unnecessary data loading
- Ensure serializers use select_related/prefetch_related appropriately
- Optimize RecipeListSerializer to exclude heavy fields

## 5. Test Performance Improvements
- Run queries before and after changes
- Use Django Debug Toolbar or similar to measure query counts
- Test with large dataset

## 6. Consider Database Migration
- Evaluate moving from SQLite to PostgreSQL for better join performance
- Update settings and requirements accordingly
