async def my_recipes_handler(message: types.Message, state: FSMContext):
    await state.set_state(UserStates.searching_results)
    user_id = message.from_user.id

    conn = await asyncpg.connect(user=DB_USER, password=DB_PASSWORD, database=DB_DATABASE, host=DB_HOST)
    try:
        user_data = await conn.fetchrow("SELECT recept_id FROM users WHERE chat_id = $1", user_id)
        if user_data and user_data['recept_id']:
            recipe_ids = [int(id) for id in user_data['recept_id'].split(',')]

            # Получаем информацию о первых трех рецептах
            recipes = await conn.fetch("SELECT id, name, bludo FROM eda WHERE id = ANY($1::int[])", recipe_ids)
            print(f"User ID: {user_id}, Recipe IDs: {recipe_ids}")

            if recipes:
                recipes_list = [dict(recipe) for recipe in recipes]
                print(f"Found recipes: {recipes}")

                for recipe in recipes[:3]:
                    image_url = recipe['bludo'].split(',')[0] if recipe['bludo'] else None
                    recipe_name = recipe['name']

                    keyboard = InlineKeyboardMarkup(row_width=2)
                    details_button = InlineKeyboardButton(text="Подробнее 🔍", callback_data=f"details_{recipe['id']}")
                    delete_recipe_button = InlineKeyboardButton(text="Удалить 🗑", callback_data=f"delete_recipe_{recipe['id']}")
                    keyboard.add(details_button, delete_recipe_button)

                    if image_url:
                        full_path = os.path.join('image', image_url)
                        with open(full_path, 'rb') as photo:
                            await message.answer_photo(photo=photo, caption=f"{recipe_name}", reply_markup=keyboard)
                    else:
                        await message.answer(f"{recipe_name}", reply_markup=keyboard)

                # Сохраняем результаты поиска и текущую страницу
                await state.update_data(search_results=recipes_list, current_page=1)

                # Отправляем клавиатуру пагинации, если есть еще результаты
                if len(recipes) > 3:
                    pagination_keyboard = InlineKeyboardMarkup(row_width=2)
                    next_button = InlineKeyboardButton("Далее➡️", callback_data="next_my_recipes")
                    pagination_keyboard.add(next_button)
                    await message.answer("Просмотреть следующие рецепты:", reply_markup=pagination_keyboard)
            else:
                await message.answer("У вас пока нет сохраненных рецептов.")
        else:
            await message.answer("У вас пока нет сохраненных рецептов.")

    except Exception as e:
        await message.answer(f"Произошла ошибка: {e}")
    finally:
        await conn.close()

    # Обработчик для кнопки пагинации "Далее"
async def next_my_recipes_handler(query: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_page = user_data.get('current_page', 1)
    recipes_list = user_data.get('search_results', [])
    results_per_page = 3

    start_index = current_page * results_per_page
    end_index = start_index + results_per_page

    if start_index < len(recipes_list):
        next_page_recipes = recipes_list[start_index:end_index]

        for recipe_dict in next_page_recipes:
            image_url = recipe_dict['bludo'].split(',')[0] if recipe_dict['bludo'] else None
            recipe_name = recipe_dict['name']

            keyboard = InlineKeyboardMarkup(row_width=2)
            details_button = InlineKeyboardButton(text="Подробнее 🔍", callback_data=f"details_{recipe_dict['id']}")
            delete_recipe_button = InlineKeyboardButton(text="Удалить 🗑", callback_data=f"delete_recipe_{recipe_dict['id']}")
            keyboard.add(details_button, delete_recipe_button)
if image_url:
                full_path = os.path.join('image', image_url)
                with open(full_path, 'rb') as photo:
                    await query.message.answer_photo(photo=photo, caption=f"{recipe_name}", reply_markup=keyboard)
            else:
                await query.message.answer(f"{recipe_name}", reply_markup=keyboard)

        if end_index < len(recipes_list):
            pagination_keyboard = InlineKeyboardMarkup(row_width=2)
            next_button = InlineKeyboardButton("Далее➡️", callback_data="next_my_recipes")
            pagination_keyboard.add(next_button)
            await query.message.answer("Просмотреть следующие рецепты:", reply_markup=pagination_keyboard)

        # Обновляем номер текущей страницы
        await state.update_data(current_page=current_page + 1)

    else:
        await query.message.answer("Больше нет рецептов.")

    await query.answer()
