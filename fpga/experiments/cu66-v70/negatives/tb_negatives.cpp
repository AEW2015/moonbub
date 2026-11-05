#define main v70_existing_main
#include "../receiver/tb_receiver.cpp"
#undef main

#include <cstdlib>

int main(int argc, char **argv) {
    try {
        need(argc == 6, "usage: tb_negatives cases.tsv native_dir seed_key recovery_key seed");
        const std::filesystem::path cases_path = argv[1];
        const std::filesystem::path native_dir = argv[2];
        const std::filesystem::path seed_key_path = argv[3];
        const std::filesystem::path recovery_path = argv[4];
        const unsigned seed = unsigned(std::stoul(argv[5]));
        std::ifstream cases(cases_path);
        need(bool(cases), "negative case TSV open");

        cu66::Bytes seed_packet = load(seed_key_path);
        cu66::Decoder seed_decoder;
        auto seed_gold = seed_decoder.receive(seed_packet);
        need(seed_gold && seed_gold->key, "manifest seed packet is not an independently decoded key");

        cu66::Bytes recovery_packet = load(recovery_path);
        cu66::Decoder recovery_decoder;
        auto recovery_gold = recovery_decoder.receive(recovery_packet);
        need(recovery_gold && recovery_gold->key && recovery_gold->id == 24,
             "manifest recovery packet is not independent key 24");

        std::string row;
        unsigned count = 0;
        while (std::getline(cases, row)) {
            if (row.empty()) continue;
            std::stringstream fields(row);
            std::string name, category, relative_path, byte_count, digest;
            std::getline(fields, name, '\t');
            std::getline(fields, category, '\t');
            std::getline(fields, relative_path, '\t');
            std::getline(fields, byte_count, '\t');
            std::getline(fields, digest, '\t');
            need(!name.empty() && !category.empty() && !relative_path.empty() &&
                 !byte_count.empty() && !digest.empty(), "malformed negative case TSV row");
            std::cout << "NEGATIVE_CASE_BEGIN name=" << name << " category=" << category
                      << " packet=" << relative_path << " bytes=" << byte_count
                      << " sha256=" << digest << std::endl;

            Sim sim(seed + count);
            sim.run(seed_packet, seed_gold);
            cu66::Bytes bad = load(native_dir / relative_path);
            need(bad.size() == std::stoul(byte_count), "fixture size changed: " + name);
            sim.run(std::move(bad), nullptr, 8);
            sim.run(recovery_packet, recovery_gold);
            std::cout << "NEGATIVE_CASE_PASS name=" << name << std::endl;
            ++count;
        }
        need(count == 1, "expected exactly one selected case, observed " + std::to_string(count));
        std::cout << "NEGATIVES_PASS cases=" << count
                  << " seed_reject_recovery=1 seed=" << seed
                  << " memory_backend=transactional_RAM painter=completion_model"
                  << " scanout=descriptor_model" << std::endl;
        return 0;
    } catch (const std::exception &error) {
        std::cerr << "NEGATIVES_FAIL " << error.what() << std::endl;
        return 1;
    }
}
