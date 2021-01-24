def get_top_K(count_dict, max_items=7, verbose=True, hide_shadowed=False):
    count_dict_ = dict(sorted(count_dict.items(), key=lambda item: item[1], reverse=True))
    top_K = set()
    for k, v in count_dict_.items():
        if verbose:
            print(k, v)
        if hide_shadowed:
            found = None
            for selected_term in top_K:
                if selected_term in k or k in selected_term:
                    found = selected_term
            if found:
                if len(k) < len(selected_term):
                    top_K.remove(selected_term)
                    top_K.add(k)
                continue
        max_items -= 1
        top_K.add(k)
        if max_items <= 0:
            break
    return top_K


def prioritize_columns(df, max_items=7, cutoff=None):
    priority_by_column = dict()

    for column, dtype in df.dtypes.items():
        if dtype == "int64":
            repetition = False
            item_counts = df[column].value_counts()
            for k, v in item_counts.items():
                if cutoff and v > cutoff:
                    repetition = Tru
            if repetition:
                print("Excluding", column, "due to repetition", repetition)
                # Rather than filter, use weighting
                continue
            priority_by_column[column] = df[column].std() / oura_data[column].mean()

    return get_top_K(priority_by_column, max_items)
