import random
import json

class StringLibrary:
    
    def format_answers_timequestions(self, instance):
        """
        Reformat answers in the timequestions dataset.
        """
        _answers = list()
        for answer in instance["Answer"]:
            if answer["AnswerType"] == "Entity":
                answer = {"id": answer["WikidataQid"], "label": answer["WikidataLabel"]}
            elif answer["AnswerType"] == "Value":
                answer = {
                    "id": answer["AnswerArgument"],
                    "label": StringLibrary.convert_timestamp_to_date(
                        answer["AnswerArgument"]) if StringLibrary.is_timestamp(answer["AnswerArgument"]) else answer[
                        "AnswerArgument"]
                }
            elif answer["AnswerType"] == "Timestamp":
                answer = {
                    "id": answer["AnswerArgument"],
                    "label": StringLibrary.convert_timestamp_to_date(
                        answer["AnswerArgument"]) if StringLibrary.is_timestamp(answer["AnswerArgument"]) else answer[
                        "AnswerArgument"]
                }
            else:
                print(answer)
                raise Exception
            _answers.append(answer)
        return _answers
    
    @staticmethod
    def convert_timestamp_to_date(timestamp):
        """Convert the given timestamp to the corresponding date."""
        try:
            adate = timestamp.rsplit("-", 2)
            # parse data
            year = adate[0]
            month = StringLibrary.convert_number_to_month(adate[1])
            day = adate[2].split("T")[0]
            # remove leading zero
            if day[0] == "0":
                day = day[1]
            if day == "1" and adate[1] == "01":
                # return year for 1st jan
                return year
            date = f"{day} {month} {year}"
            return date
        except:
            #print(f"Failure with timestamp {timestamp}")
            return timestamp
    
    @staticmethod
    def convert_number_to_month(number):
        """Map the given month to a number."""
        return {
            "01": "January",
            "02": "February",
            "03": "March",
            "04": "April",
            "05": "May",
            "06": "June",
            "07": "July",
            "08": "August",
            "09": "September",
            "10": "October",
            "11": "November",
            "12": "December",
        }[number]


    @staticmethod
    def sample_train_timequestions(file_path, output_file_path):
        with open(file_path, 'r') as file:
            data = json.load(file)

        # Function to balance and sample data
        def sample_balanced_data(data, sample_size):
            # Group data by temporal question type
            type_dict = {}
            for item in data:
                question_type = item["temporal question type"][0]
                if question_type not in type_dict:
                    type_dict[question_type] = []
                type_dict[question_type].append(item)
            
            # Calculate how many samples per type
            types = list(type_dict.keys())
            num_types = len(types)
            samples_per_type = sample_size // num_types

            # Sample data
            sampled_data = []
            for question_type in types:
                sampled_data.extend(random.sample(type_dict[question_type], min(samples_per_type, len(type_dict[question_type]))))
            
            return sampled_data

        # Sample 200 balanced data points
        sampled_data = sample_balanced_data(data, 200)

        # Save the sampled data to a new JSON file
        with open(output_file_path, 'w') as output_file:
            json.dump(sampled_data, output_file, indent=4)

        print(f'Sampled data saved to {output_file_path}')


if __name__ == "__main__":
    path_file = "/mnt/media_1/guest22/ldy/cok/datasets/timequestions/train.json"
    output_file_path = "/mnt/media_1/guest22/ldy/cok/datasets/timequestions/train_sample.json"
    StringLibrary.sample_train_timequestions(path_file, output_file_path)















